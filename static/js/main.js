import './delete_message'
import './modification_message'


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
