const messagesContainer = $("#messages-container");
const roomId = messagesContainer.data("room-id");
export const state = { isEditing: false };

function scrollToBottom() {
    messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
}

export function getMessages() {
    if (roomId) {
        $.ajax({
            url: `/room/${roomId}/get_messages/`,
            method: 'GET',
            success: function (data) {
                if (data.html_message) {
                    messagesContainer.empty();
                    let parsed_html = data.html_message.replace(/&lt;br&gt;/g, '<br>');
                    messagesContainer.append(parsed_html);
                    scrollToBottom();
                }
            },
            error: function () {
                console.error('Erreur lors de la récupération des messages.');
            }
        });
    }
}

$(document).ready(function () {
    $('#msg').on('input', function () {
        const sendButton = $('.send-btn');
        sendButton.prop('disabled', !$(this).val().trim().length);
    });

    $('.send-btn').on('click', function (e) {
        e.preventDefault();
        const message = $('#msg').val().trim();
        if (message) {
            $.ajax({
                url: `/room/${roomId}/send_message/`,
                method: 'POST',
                headers: {'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()},
                data: {content: message},
                success: function () {
                    $('#msg').val('');
                    getMessages();
                },
                error: function () {
                    console.error('Erreur lors de l\'envoi du message.');
                }
            });
        }
    });

    getMessages();
    scrollToBottom();
});