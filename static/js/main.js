let popovers = document.querySelectorAll('#popover')

popovers.forEach((popover) => {
    new bootstrap.Popover(popover, {
        trigger: 'focus'
    });
});