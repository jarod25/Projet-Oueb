// This script is used to make an AJAX request to the server to get a list of usernames that match the query entered by the user in the receiver field.

let lastMessageId = null; // Variable pour suivre le dernier ID de message

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
    
    setInterval(function(){
        $( ".message" ).load(window.location.href + " .message" );
    }, 2000)
    
});

$(document).on('submit', '#message', function(e){
    e.preventDefault();
    $.ajax({
        type: 'POST',
        url: "",
        data: {
            message: $('#msg').val(),
            csrfmiddlewaretoken: $('input[name=csrfmiddlewaretoken]').val()
        }
    });
    $( ".message-container" ).load(window.location.href + " .message-container" );
})