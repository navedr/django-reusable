const DjangoReusableAdminUtils = {
    init: function ({isChangelist, isChangeForm}) {
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
        const self = this;
        fetch("{{ admin_utils_url }}", {
            method: 'POST',
            body: JSON.stringify({
                app,
                model,
                isChangelist,
                isChangeForm,
            })
        }).then(response => response.json()).then(data => {
            if (isChangelist) {
                self.initChangelist(data);
            } else if (isChangeForm) {
                self.initChangeForm(data);
            }
        });
    },
    initChangelist: function (data) {
    },
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
