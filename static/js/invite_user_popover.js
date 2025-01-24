$(document).ready(function () {
    function closeAllPopovers() {
        $('.popover').remove();
    }

    function adjustPopover($trigger) {
        const $popover = $('.popover');
        if ($(window).width() <= 432) {
            $popover.css({
                position: 'absolute',
                top: $trigger.offset().top + 104,
                left: 0,
                zIndex: 1046
            });
        } else if ($(window).width() < 768) {
            $popover.css({
                position: 'absolute',
                top: $trigger.offset().top + 104,
                left: $trigger.offset().left - 190,
                zIndex: 1046
            });
        } else {
            $popover.css({
                position: 'absolute',
                top: $trigger.offset().top,
                left: $trigger.offset().left - 418,
                zIndex: 1000
            });
        }
    }

    $('#invitePopover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
        closeAllPopovers();
        $.ajax({
            url: 'invite_user',
            method: 'GET',
            success: function (response) {
                const $popover = $(response).addClass('popover shadow p3');
                $popover.appendTo('body');
                adjustPopover($trigger);
            }
        });
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.popover, .open-user-popover').length) {
            closeAllPopovers();
        }
    });
});