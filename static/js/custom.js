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

// Script used to make an AJAX request to the server to get the messages of a room and display them in the chat.
$(document).ready(function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    function getMessages() {
        $.ajax({
            url: `/room/${roomId}/get_messages/`,
            method: 'GET',
            success: function (data) {
                messagesContainer.empty();
                let parsed_html = data.html_message.replace('&lt;br&gt;', '<br>');
                messagesContainer.append(parsed_html);
            },
            error: function (xhr, status, error) {
                console.error('Erreur lors de la récupération des messages :', status, error);
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
            },
        });
    }

    // TODO: repair
    $('#msg').on('input', function () {
        const sendButton = $('.send-button');
        if ($(this).val().length > 0) {
            sendButton.removeAttr('disabled');
        } else {
            sendButton.attr('disabled', 'disabled');
        }
    });

    $('.send-button').on('click', async function (e) {
        e.preventDefault();
        try {
            await sendMessage();
            setTimeout(getMessages, 100);
        } catch (error) {
            console.error('Erreur dans la chaîne d\'exécution:', error);
        }
    });
});
