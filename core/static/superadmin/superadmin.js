(function ($) {

    $("button.index-control").click(function () {
        let button = $(this);
        let form = button.parents('form');

        form.find('input[name=index_name]').val(button.data('index-name'))
        form.find('input[name=task]').val(button.data('task'))
        form.submit();
    });

})(jQuery);
