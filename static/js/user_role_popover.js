$(document).ready(function () {
    function toggleUserButton() {
        if ($(window).width() < 768) {
            $('#mobile-users-button').show();
            $('#desktop-users-column').hide();
        } else {
            $('#mobile-users-button').hide();
            $('#desktop-users-column').show();
        }
    }

    toggleUserButton();

    $(window).on('resize', function () {
        toggleUserButton();
    });

    $('#mobile-users-button').on('click', function () {
        $('#usersOffcanvas').offcanvas('show');
    });

    function closeAllPopovers() {
        $('.popover').remove();
        $('#user-btn').removeClass('active');
    }

    function adjustPopover($trigger) {
        const $popover = $('.popover');
        if ($(window).width() < 768) {
            $popover.css({
                position: 'absolute',
                top: $trigger.offset().top + 50,
                left: $trigger.offset().left,
                zIndex: 1046
            });
        } else {
            $popover.css({
                position: 'absolute',
                top: $trigger.offset().top,
                left: $trigger.offset().left - 210,
                zIndex: 1000
            });
        }
    }

    function transformRole(role) {
        switch (role) {
            case 'owner':
                return 'Propriétaire';
            case 'administrator':
                return 'Administrateur';
            case 'user':
                return 'Utilisateur';
            case 'muted':
                return 'Muet';
            default:
                return 'Inconnu';
        }
    }

    $('.open-user-popover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
        const userId = $trigger.data('id');
        const username = $trigger.data('username');
        let role = $trigger.data('role');
        const $userItem = $trigger.find('#user-btn');
        closeAllPopovers();
        $userItem.addClass('active');

        $.ajax({
            url: 'user_role_popover',
            method: 'GET',
            data: {user_id: userId},
            success: function (response) {
                const $popover = $(response).addClass('popover shadow p-3');
                $('body').append($popover);
                adjustPopover($trigger);
                $popover.find('#popover-username').text(username);
                role = transformRole(role);
                $popover.find('#popover-role-display').text(role);

                const canAct = $popover.data('can-act');
                const isTargetOwner = $popover.data('is-target-owner');

                if (!canAct || isTargetOwner) {
                    $popover.find('#popover-action, #savePopoverRole, #mute-duration-container').parent().remove();
                }

                $popover.find('#savePopoverRole').on('click', function () {
                    const action = $popover.find('#popover-action').val();
                    const muteDuration = $popover.find('#popover-mute-duration').val();

                    $.ajax({
                        url: 'update_user_role/',
                        method: 'POST',
                        data: {
                            user_id: userId,
                            action: action,
                            mute_duration: muteDuration,
                            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
                        },
                        success: function () {
                            alert('Action effectuée avec succès.');
                            closeAllPopovers();
                            location.reload();
                        },
                        error: function (xhr) {
                            alert('Erreur lors de l\'exécution de l\'action : ' + (xhr.responseJSON?.error || ''));
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

    $(document).on('change', '#popover-action', function () {
        const action = $(this).val();
        if (action === 'mute') {
            $('#mute-duration-container').show();
            $('#popover-mute-duration').attr('required', true);
        } else {
            $('#mute-duration-container').hide();
            $('#popover-mute-duration').removeAttr('required');
        }
    });
});