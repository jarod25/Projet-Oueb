const messagesContainer = $("#messages-container");
const roomId = messagesContainer.data("room-id");
export const state = { isEditing: false };

function scrollToBottom() {
    messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
}

let lastMessageTime = null;
let isPolling = false;

export function getMessages() {
    if (roomId && !isPolling) {
        isPolling = true;
        const params = lastMessageTime ? `?last_message_time=${encodeURIComponent(lastMessageTime)}` : "";
        $.ajax({
            url: `/room/${roomId}/get_messages/${params}`,
            method: 'GET',
            success: function (data) {
                if (data.html_message) {
                    let parsed_html = data.html_message.replace(/&lt;br&gt;/g, '<br>');
                    messagesContainer.append(parsed_html);
                    scrollToBottom();
                    lastMessageTime = data.latest_message_time;
                }
                isPolling = false;
                getMessages();
            },
            error: function (xhr, status, error) {
                console.info('Error while polling messages:', error);
                isPolling = false;
                setTimeout(getMessages, 3000);
            }
        });
    }
}


$(document).ready(function () {
    getMessages();
    scrollToBottom();

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
                    alert('Erreur lors de l\'envoi du message.');
                }
            });
        }
    });
});