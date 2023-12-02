const DjangoReusableAdminUtils = {
    init: function ({ isChangelist, isChangeForm }) {
        let app, model;
        const paths = location.pathname.split("/").filter(s => !!s);
        if (isChangelist) {
            app = paths[paths.length - 2];
            model = paths[paths.length - 1];
        } else if (isChangeForm) {
            if (paths[paths.length - 1] === "add") {
                // host/<app>/<model>/add/
                app = paths[paths.length - 3];
                model = paths[paths.length - 2];
            } else {
                // host/<app>/<model>/<pk>/change/
                app = paths[paths.length - 4];
                model = paths[paths.length - 3];
            }
        }
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
