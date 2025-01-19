$(document).ready(function () {
    function closeAllPopovers() {
        $('.popover').remove();
        $('#user-btn').removeClass('active');
    }

    $('.open-user-popover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
        const userId = $trigger.data('id');
        const username = $trigger.data('username');
        const role = $trigger.data('role');
        const $userItem = $trigger.find('#user-btn');
        closeAllPopovers();
        $userItem.addClass('active');

        $.ajax({
            url: 'user_role_popover',
            method: 'GET',
            success: function (response) {
                const $popover = $(response).addClass('popover shadow p-3').css({
                    position: 'absolute',
                    top: $trigger.offset().top,
                    left: $trigger.offset().left - 210,
                    zIndex: 1000
                });

                $('body').append($popover);
                $popover.find('#popover-username').text(username);
                $popover.find('#popover-role').val(role);
                $popover.find('#savePopoverRole').on('click', function () {
                    const newRole = $popover.find('#popover-role').val();
                    $.ajax({
                        url: 'update_user_role/',
                        method: 'POST',
                        data: {
                            user_id: userId,
                            role: newRole,
                            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
                        },
                        success: function () {
                            alert('Rôle mis à jour avec succès.');
                            closeAllPopovers();
                            location.reload();
                        },
                        error: function () {
                            alert('Erreur lors de la mise à jour.');
                        }
                    });
                });
            },
            error: function () {
                alert('Erreur lors du chargement du contenu.');
            }
        });
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.popover, .open-user-popover').length) {
            closeAllPopovers();
        }
    });
});