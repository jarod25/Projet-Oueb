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

    // Load messages and handle message submission
    let lastMessageId = null; // Track the ID of the last displayed message
/*
    function loadMessages(clearContainer = false) {
        $.ajax({
            url: window.location.href, // Use the current URL
            data: { last_id: lastMessageId || 0 }, // Pass the last message ID (or 0 if null)
            success: function (data) {
                if (data.new_messages && data.new_messages.length > 0) {
                    const messageContainer = $(".messages-container");

                    // Clear the container if `clearContainer` is true (e.g., on page refresh)
                    if (clearContainer) {
                        messageContainer.empty();
                    }

                    // Append each new message to the container
                    data.new_messages.forEach(function (message) {
                        messageContainer.append(`
                            <div class="message" data-message-id="${message.id}">
                                <p>
                                    <strong>${message.author}</strong>
                                    ${message.timestamp}<br>
                                    ${message.content}
                                </p>
                                <button class="delete-message btn btn-sm btn-danger" data-delete-url="${message.delete_url}" title="Supprimer ce message">
                                    <i class="bi bi-trash-fill"></i> Supprimer
                                </button>
                            </div>
                        `);
                        lastMessageId = message.id; // Update the last message ID
                    });
                }
            },
        });
    }
*/
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
                loadMessages(false); // Fetch new messages immediately after sending
            },
        });
    });

    // Load messages on page load (clearContainer = true ensures no duplicates)
    loadMessages(true);

    // Fetch new messages every 2 seconds (clearContainer = false to append new ones only)
    setInterval(function () {
        loadMessages(false);
    }, 2000);
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

$(document).on("click", ".delete-message", function (e) {
    e.preventDefault();
    const button = $(this);
    const deleteUrl = button.data("delete-url");
    console.log(deleteUrl)

    if (confirm("Voulez-vous vraiment supprimer ce message ?")) {
        $.ajax({
            url: deleteUrl,
            type: "POST",
            data: {
                csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val(),
            },
            success: function () {
                // Supprimer le message du DOM après suppression
                button.closest(".message").remove();
            },
            error: function () {
                alert("Une erreur s'est produite lors de la suppression du message.");
            },
        });
    }
});
