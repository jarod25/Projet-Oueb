const messagesContainer = $("#messages-container");
const roomId = messagesContainer.data("room-id");
export const state = {isEditing: false};

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
                if (data.messages) {
                    data.messages.forEach(message => {
                        const existingMessage = $(`#message-line[data-message-id="${message.id}"]`);

                        if (message.is_deleted) {
                            if (existingMessage.length) {
                                existingMessage.remove();
                            }
                        } else {
                            let parsed_html = message.html.replace(/&lt;br&gt;/g, '<br>');
                            if (existingMessage.length) {
                                existingMessage.replaceWith(parsed_html);
                            } else {
                                messagesContainer.append(parsed_html);
                            }
                        }
                    });
                    scrollToBottom();
                    lastMessageTime = data.latest_message_time;
                }
                isPolling = false;
                getMessages();
            },
            error: function () {
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