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
});

// Script used to make an AJAX request to the server to get the messages of a room and display them in the chat.
$(document).ready(function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    function scrollToBottom() {
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }

    if (roomId) {
        function getMessages() {
            $.ajax({
                url: `/room/${roomId}/get_messages/`,
                method: 'GET',
                success: function (data) {
                    if (data.html_message) {
                        messagesContainer.empty();
                        let parsedHtml = data.html_message.replace('&lt;br&gt;', '<br>');
                        messagesContainer.append(parsedHtml);
                        scrollToBottom();
                    }
                    getMessages();
                },
                error: function (xhr, status, error) {
                    console.error('Erreur lors de la récupération des messages :', status, error);
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
