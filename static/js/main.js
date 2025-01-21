// This script is used to make an AJAX request to the server to get a list of usernames that match the query entered by the user in the receiver field.
$(document).ready(function () {
    $(document).on('input', '#receiver', function () {
        let query = $(this).val();
        let roomId = $(this).closest('form').data('room-id');
        let infos = $('#infos');
        if (query.length > 1) {
            $.ajax({
                url: `/room/${roomId}/invite/search_users`,
                data: {'q': query},
                success: function (data) {
                    let suggestionsList = $('#suggestions-list');
                    suggestionsList.empty();
                    if (data.length > 0) {
                        data.forEach(function (user) {
                            suggestionsList.append(`
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${user.username}
                                    <button class="btn btn-primary btn-sm invite-btn" data-user-id="${user.id}">Inviter</button>
                                </li>
                            `);
                        });
                    } else {
                        suggestionsList.append('<li class="list-group-item text-muted">Aucun utilisateur trouvé</li>');
                    }
                },
                error: function () {
                    infos.text('Erreur lors de la recherche des utilisateurs.');
                    infos.removeClass('text-success').addClass('text-danger');
                }
            });
        } else {
            $('#suggestions-list').empty();
        }
    });

    $(document).on('click', '.invite-btn', function (e) {
        e.preventDefault();
        let userId = $(this).data('user-id');
        let roomId = $(this).closest('form').data('room-id');
        let infos = $('#infos');

        $.ajax({
            url: `/room/${roomId}/invite/`,
            method: 'POST',
            headers: {'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()},
            data: {
                'receiver_id': userId
            },
            success: function (response) {
                infos.text(response.message);
                infos.removeClass('text-danger').addClass('text-success');
            },
            error: function (xhr) {
                let errorMsg = xhr.responseJSON?.error || 'Erreur lors de l\'invitation.';
                infos.text(errorMsg);
                infos.removeClass('text-success').addClass('text-danger');
            }
        });
    });

    $(document).on('click', '.btn-close', function () {
        $('#receiver').val('');
        $('#suggestions-list').empty();
    });
});

// Script used to make the textarea grow as the user types in it.
$(document).ready(function () {
    $('#input-text').on('input', function () {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        this.style.zIndex = '0';
    });
});

// Script used to make an AJAX request to the server to get the messages of a room and display them in the chat.
$(document).ready(function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    let isEditing = false; // Flag to track editing state

    function scrollToBottom() {
        if (!isEditing) { // Scroll only if not editing
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        }
    }


    if (roomId) {
        function getMessages() {
            if (isEditing) return;
            $.ajax({
                url: `/room/${roomId}/get_messages/`,
                method: 'GET',
                success: function (data) {
                    if (data.html_message) {
                        const parsedHtml = $("<div>").html(data.html_message.replace('&lt;br&gt;', '<br>'));
                        const newMessageIds = [];

                        parsedHtml.find("#message-line").each(function () {
                            newMessageIds.push($(this).data("message-id"));
                        });

                        messagesContainer.find("#message-line").each(function () {
                            const messageId = $(this).data("message-id");
                            if (!newMessageIds.includes(messageId)) {
                                $(this).remove();
                            }
                        });

                        messagesContainer.html(parsedHtml.html());

                        scrollToBottom();
                    }

                    setTimeout(getMessages, 1000);
                },
                error: function (xhr, status, error) {
                    console.error("Erreur lors de la récupération des messages :", status, error);

                    setTimeout(getMessages, 1000);
                }
            });

        }

        function getCSRFToken() {
            return $('input[name="csrfmiddlewaretoken"]').val();
        }

        function sendMessage() {
            const message = $('#msg').val();
            $.ajax({
                url: `/room/${roomId}/send_message/`,
                method: 'POST',
                headers: {'X-CSRFToken': getCSRFToken()},
                data: {content: message},
                success: function () {
                    $('#msg').val('');
                    scrollToBottom();
                },
            });
        }

        

        $('#msg').on('input', function () {
            const sendButton = $('.send-btn');
            if ($(this).val().length > 0) {
                sendButton.removeAttr('disabled');
            } else {
                sendButton.attr('disabled', 'disabled');
            }
        });

        $('.send-btn').on('click', function (e) {
            e.preventDefault();
            sendMessage();
        });


        getMessages();
        scrollToBottom();

    }

    $(document).on("click", "#delete-message", function (e) {
        e.preventDefault();
        const button = $(this);
        const messageLine = button.closest("#message-line");
        const messageId = messageLine.data("message-id");
    
        if (messageId) {
            $.ajax({
                url: `/room/${messageId}/delete-message/`,
                type: "POST",
                data: {
                    csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
                },
                success: function () {
                    setTimeout(getMessages, 1000);
                    messageLine.remove();
                    getMessages()
                },
                error: function () {
                    alert("Une erreur s'est produite lors de la suppression du message.");
                },
            });
        }
    });

    $(document).on("click", "#edit-message", function (e) {
        e.preventDefault();
        isEditing = true; // Set editing flag
        const button = $(this);
        const messageLine = button.closest("#message-line");
        const messageId = messageLine.data("message-id");
        const messageContent = messageLine.find(".text-break").text().trim();
        // Save original content for restoration if canceled
        messageLine.data("original-content", messageContent);
        getMessages()
        // Replace the message content with a textarea and buttons
        messageLine.find(".text-break").html(`
        <textarea class="edit-textarea form-control mb-2">${messageContent}</textarea>
        <button class="save-edit-button btn btn-sm btn-primary">Enregistrer</button>
        <button class="cancel-edit-button btn btn-sm btn-secondary">Annuler</button>
    `);
    });
    
    $(document).on("click", ".cancel-edit-button", function (e) {
        e.preventDefault();
        isEditing = false; // Reset editing flag
        const messageLine = $(this).closest("#message-line");
        const originalContent = messageLine.data("original-content");
    
        // Restore the original content
        messageLine.find(".text-break").text(originalContent);
    });
    
    $(document).on("click", ".save-edit-button", function (e) {
        e.preventDefault();
        const button = $(this);
        const messageLine = button.closest("#message-line");
        const messageId = messageLine.data("message-id");
        const newContent = messageLine.find(".edit-textarea").val();
        getMessages()
        $.ajax({
            url: `/room/${messageId}/edit-message/`,
            type: "POST",
            data: {
                csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
                content: newContent,
            },
            success: function (response) {
                isEditing = false; // Reset editing flag after save
                getMessages()
                messageLine.find(".text-break").text(response.content);
                getMessages()
            },
            error: function () {
                isEditing = false;
                getMessages()
                alert("Erreur lors de la modification du message.");
            }
        });
        getMessages();
    });
});

$(document).ready(function () {
    $('.invite-user-btn').on('click', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');
        $.get(url, function (data) {
            $('#inviteUserModal .modal-body').html(data);
            $('#inviteUserModal').modal('show'); // Affiche la modal
        }).fail(function () {
            alert('Erreur lors du chargement. Veuillez réessayer.');
        });
    });
});
