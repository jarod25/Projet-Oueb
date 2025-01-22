$(document).ready(function () {
    function closeAllPopovers() {
        $('.popover').remove();
    }

    $('#invitePopover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
        closeAllPopovers();
        $.ajax({
            url: 'invite_user',
            method: 'GET',
            success: function (response) {
                const $popover = $(response)
                    .addClass('popover shadow p3')
                    .css({
                        position: 'absolute',
                        top: $trigger.offset().top,
                        left: $trigger.offset().left - 418,
                        zIndex: 1000
                    });
                $popover.appendTo('body');
            }
        });
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.popover, .open-user-popover').length) {
            closeAllPopovers();
        }
    });
});