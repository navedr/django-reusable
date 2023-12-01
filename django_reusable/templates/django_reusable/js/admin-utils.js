const DjangoReusableAdminUtils = {
    init: function ({ isChangelist, isChangeForm }) {
        const [_, app, model] = location.pathname.split("/");
        $.ajax({
            url: "{{ admin_utils_url }}",
            method: "POST",
            data: {
                app,
                model,
                isChangelist,
                isChangeForm,
            },
            success: $.proxy(function (data) {
                $("body").addClass("django-reusable-admin");
                if (isChangelist) {
                    this.initChangelist(data);
                } else if (isChangeForm) {
                    this.initChangeForm(data);
                }
            }, this),
        });
    },
    initChangelist: function (data) {},
    initChangeForm: function (data) {
        if (data.hide_save_buttons) {
            $(".submit-row").remove();
        }
    },
};

$(document).ready(function () {
    const isChangelist = !!$("#changelist").size();
    const isChangeForm = $("body").hasClass("change-form");
    if (isChangelist || isChangeForm) {
        DjangoReusableAdminUtils.init({
            isChangelist,
            isChangeForm,
        });
    }
});
