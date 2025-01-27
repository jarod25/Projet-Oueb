const messagesContainer = $("#messages-container");
const roomId = messagesContainer.data("room-id");
export const state = {isEditing: false};

function scrollToBottom() {
    messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
}

let lastMessageTime = null;
let isPolling = false;

export function getMessages() {
    console.log(roomId);
    console.log('getMessages');
    if (typeof roomId !== 'undefined' && !isPolling) {
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
                if (typeof roomId !== 'undefined') {
                    setTimeout(getMessages, 3000);
                }
            }
        });
    }
}

export function replaceEmoji(text) {
    const emojiMap = {
        ':-)': '😊', ':)': '😊',
        ':-(': '☹️', ':(': '☹️',
        ';-)': '😉', ';)': '😉',
        ':-D': '😁', ':D': '😁',
        ':-P': '😛', ':P': '😛',
        ':-p': '😛', ':p': '😛',
        ':-O': '😮', ':O': '😮',
        ':-o': '😮', ':o': '😮',
        ':-|': '😐', ':|': '😐',
        ':-/': '😕', ':/': '😕',
        ':-\\': '😕', ':\\': '😕',
        ':-*': '😘', ':*': '😘',
        '<3': '❤️',
        '</3': '💔',
        ':-X': '🤐', ':X': '🤐',
        ':-x': '🤐', ':x': '🤐',
        ':-$': '🤑', ':$': '🤑',
        ':-@': '😡', ':@': '😡',
        ':-!': '😮‍💨', ':!': '😮‍💨',
        ':-Z': '😴', ':Z': '😴',
        ':-z': '😴', ':z': '😴',
        'B-)': '😎', 'B)': '😎',
        ':-]': '😏', ':]': '😏',
        ':-[': '😔', ':[': '😔',
        ':-{': '😖', ':{': '😖',
        ':-}': '😌', ':}': '😌',
        ':@)': '🦄',
        'O:-)': '😇', 'O:)': '😇',
        '3:-)': '😈', '3:)': '😈',
        ':-E': '😬', ':E': '😬',
        ':3': '🐱',
        '8-)': '😎', '8)': '😎',
        ':-B': '🤓', ':B': '🤓',
        ':-C': '😵', ':C': '😵',
        ':|]': '😼',
        ':^)': '🤔',
        ':rolleyes:': '🙄',
        ':shrug:': '🤷',
        ':mindblown:': '🤯',
        ':sweat:': '😓',
        ':yawn:': '🥱',
        ':zzz:': '💤',
        ':nerd:': '🤓',
        ':star:': '⭐',
        ':fire:': '🔥',
        ':poop:': '💩',
        ':wave:': '👋',
        ':thumbsup:': '👍',
        ':thumbsdown:': '👎',
        ':ok:': '👌',
        ':clap:': '👏',
        ':pray:': '🙏',
        ':wink:': '😉',
        ':joy:': '😂',
        ':sob:': '😭',
        ':angry:': '😠',
        ':kiss:': '😘',
        ':heart:': '❤️',
        ':brokenheart:': '💔',
        ':eyes:': '👀',
        ':clown:': '🤡',
        ':rofl:': '🤣',
    };

    // Replace each smiley using the map
    const regex = new RegExp(Object.keys(emojiMap).map(key => key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'), 'g');
    return text.replace(regex, match => emojiMap[match] || match);
}


$(document).ready(function () {
    console.log(roomId);
    console.log('sendMessages');
    if (typeof roomId !== 'undefined') {
        getMessages();
        scrollToBottom();

        $('#msg').on('input', function () {
            const sendButton = $('.send-btn');
            sendButton.prop('disabled', !$(this).val().trim().length);
        });

        $('.send-btn').on('click', function (e) {
            e.preventDefault();
            let message = $('#msg').val().trim();
            message = replaceEmoji(message); // Capturez le retour ici
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
    }
});