// This script is used to make an AJAX request to the server to get a list of usernames that match the query entered by the user in the receiver field.
$(document).ready(function () {
    $('#receiver').on('input', function () {
        let query = $(this).val();
        if (query.length > 1) {
            $.ajax({
                url: 'search_users',
                data: {'q': query},
                success: function (data) {
                    $('#suggestions-list').empty();
                    data.forEach(function (username) {
                        $('#suggestions-list').append('<li>' + username + '</li>');
                    });
                }
            });
        } else {
            $('#suggestions-list').empty();
        }
    });

    $(document).on('click', '#suggestions-list li', function () {
        $('#receiver').val($(this).text());
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

    let messagesContainer = $('#input-container');
    messagesContainer.scrollTop(messagesContainer.prop("scrollHeight"));
});

$(document).ready(function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    let isEditing = false; // Flag to track editing state

    function scrollToBottom() {
        if (!isEditing) { // Scroll only if not editing
            const messagesContainer = $("#messages-container");
            messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
        }
    }

    function getMessages() {
        if (isEditing) return; // Skip refresh if editing

        const messagesContainer = $("#messages-container");
        const roomId = messagesContainer.data("room-id");

        $.ajax({
            url: `/room/${roomId}/get_messages/`,
            method: 'GET',
            success: function (data) {
                if (data.html_message) {
                    const parsedHtml = $("<div>").html(data.html_message);
                    const newMessageIds = [];
                    parsedHtml.find(".message-line").each(function () {
                        newMessageIds.push($(this).data("message-id"));
                    });

                    messagesContainer.find(".message-line").each(function () {
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
                console.error("Error fetching messages:", status, error);
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
        const sendButton = $('.send-button');
        if ($(this).val().length > 0) {
            sendButton.removeAttr('disabled');
        } else {
            sendButton.attr('disabled', 'disabled');
        }
    });

    $('.send-button').on('click', function (e) {
        e.preventDefault();
        sendMessage();
    });

    $(document).on("click", "#delete-message", function (e) {
        e.preventDefault();
        const button = $(this);
        const messageLine = button.closest(".message-line");
        const messageId = messageLine.data("message-id");

        if (messageId) {
            $.ajax({
                url: `/room/${messageId}/delete-message/`,
                type: "POST",
                data: {
                    csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
                },
                success: function () {
                messageLine.remove();
                messageLine.remove();

                    messageLine.remove();

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
        const messageLine = button.closest(".message-line");
        const messageId = messageLine.data("message-id");
        const messageContent = messageLine.find(".message-content").text().trim();

        // Save original content for restoration if canceled
        messageLine.data("original-content", messageContent);

        // Replace the message content with a textarea and buttons
        messageLine.find(".message-content").html(`
            <textarea class="edit-textarea form-control mb-2">${messageContent}</textarea>
            <button class="save-edit-button btn btn-sm btn-primary">Enregistrer</button>
            <button class="cancel-edit-button btn btn-sm btn-secondary">Annuler</button>
        `);
    });

    $(document).on("click", ".cancel-edit-button", function (e) {
        e.preventDefault();
        isEditing = false; // Reset editing flag
        const messageLine = $(this).closest(".message-line");
        const originalContent = messageLine.data("original-content");

        // Restore the original content
        messageLine.find(".message-content").text(originalContent);
    });

    $(document).on("click", ".save-edit-button", function (e) {
        e.preventDefault();
        const button = $(this);
        const messageLine = button.closest(".message-line");
        const messageId = messageLine.data("message-id");
        const newContent = messageLine.find(".edit-textarea").val();

        $.ajax({
            url: `/room/${messageId}/edit-message/`,
            type: "POST",
            data: {
                csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
                content: newContent,
            },
            success: function (response) {
                isEditing = false; // Reset editing flag after save
                messageLine.find(".message-content").text(response.content);
            },
            error: function () {
                alert("Erreur lors de la modification du message.");
            }
        });
        getMessages();
    });

    // Initialize message fetching
    getMessages();
    scrollToBottom();
});
