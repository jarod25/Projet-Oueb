

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
    let lastMessageId = null; // Track the ID of the last displayed message

    function fetchMessages() {
        $.ajax({
            url: window.location.href, // Use the current URL
            data: { last_id: lastMessageId }, // Pass the last message ID
            success: function (data) {
                // Assuming the server returns only new messages in JSON format
                if (data.new_messages && data.new_messages.length > 0) {
                    data.new_messages.forEach(function (message) {
                        // Append each new message to the message-container
                        $(".messages-container").append(`
                            <div class="message">
                                <p>
                                    <strong>${message.author}</strong>
                                    ${message.timestamp}<br>
                                    ${message.content}
                                </p>
                            </div>
                        `);
                        lastMessageId = message.id; // Update the last message ID
                    });
                }
            },
        });
    }

    // Fetch new messages every 2 seconds
    setInterval(fetchMessages, 500);

    // Handle message submission
    $(document).on("submit", "#message", function (e) {
        e.preventDefault();
        $.ajax({
            type: "POST",
            url: $(this).attr("action"),
            data: {
                content: $("#msg").val(),
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            },
            success: function () {
                // Clear the input field after sending the message
                $("#msg").val("");
                fetchMessages(); // Optionally fetch immediately after sending
            },
        });
    });
});
