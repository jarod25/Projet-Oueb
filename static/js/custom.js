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
    $('.send-button').on('click', function () {

    });
});

$(document).on('click', '.send-button', function () {
    const messagesContainer = $("#messages-container");
    const roomId = messagesContainer.data("room-id");

    function pollNewMessages() {
        const lastMessageId = messagesContainer.data("last-id");

        $.ajax({
            url: `/room/${roomId}/new_messages/`,
            method: "GET",
            data: { last_id: lastMessageId },
            success: function (data) {
                if (data.new_messages) {
                    let parsed_html = data.html_message.replace('&lt;br&gt;', '<br>');
                    messagesContainer.append(parsed_html);
                    messagesContainer.data("last-id", data.last_id);
                }
                // pollNewMessages();
            },
            error: function () {
                setTimeout(pollNewMessages, 1000);
            },
        });
    }

    pollNewMessages();

    $("#message").on("submit", function (e) {
        e.preventDefault();

        $.ajax({
            url: $(this).attr("action"),
            method: "POST",
            data: $(this).serialize(),
            success: function () {
                $("#msg").val("");
            },
            error: function (xhr, status, error) {
                console.error("Erreur lors de l'envoi du message :", status, error);
            },
        });
    });
});

