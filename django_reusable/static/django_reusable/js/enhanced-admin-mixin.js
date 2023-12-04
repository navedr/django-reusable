const EnhancedAdminMixin = {
    init: function ({isChangelist, isChangeForm}) {
        const self = this;
        fetch(`${location.pathname}dr-admin-mixin-js-data`)
            .then(response => response.json()).then(data => {
            if (!data.enabled) {
                return;
            }
            $("body").addClass("enhanced-admin");
            if (isChangelist) {
                self.initChangelist(data);
            } else if (isChangeForm) {
                self.initChangeForm(data);
            }
            self.handleAjaxFields();
        });
    },
    initChangelist: function (data) {
        data.extra_links.forEach(({url, config: {link_class, new_tab, link_text}}) => {
            $("ul.breadcrumb").append(
                `<li>
                    <span class="divider">|</span>
                    <a href="${url}" class="btn ${link_class}" target="${new_tab ? "_blank" : ""}">${link_text}</a>
                </li>`,
            );
        });
    },
    initChangeForm: function (data) {
        if (data.hide_save_buttons) {
            $(".submit-row").remove();
        } else {
            data.extra_submit_buttons.forEach(({name, config: {btn_text, btn_class}}) => {
                $(".submit-row").append(
                    `<button name="__${name}" type="submit" class="btn ${btn_class}">${btn_text}</button>`,
                );
            });
        }
    },
    handleAjaxFields: function () {
        $(".dr-ajax-action-btn").click(function (e) {
            fetch($(e.currentTarget).data("url"))
                .then(response => response.text())
                .then(response => alert(response))
                .catch(response => {
                    console.log(response);
                    alert("Error while performing this action!")
                });
            return false;
        });
    },
};

$(document).ready(function () {
    const isChangelist = !!$("#changelist").size();
    const isChangeForm = $("body").hasClass("change-form");
    if (isChangelist || isChangeForm) {
        EnhancedAdminMixin.init({
            isChangelist,
            isChangeForm,
        });
    }
});
