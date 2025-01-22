$(document).ready(function () {
    function closeAllPopovers() {
        $('.popover').remove();
    }

    $('#invitePopover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.popover, .open-user-popover').length) {
            closeAllPopovers();
        }
    });
});