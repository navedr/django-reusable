const EnhancedAdminMixin = {
    init: function () {
        $.ajax({
            url: `${location.pathname}dr-admin-mixin-js-data`,
            success: $.proxy(function (data) {
                console.log(data)
                if (!data.enabled) {
                    return;
                }
                if ($("#changelist").size()) {
                    this.initChangelist(data);
                } else if ($("body").hasClass("change-form")) {
                    this.initChangeForm(data);
                }
            }, this)
        })
    },
    initChangelist: function (data) {
        data.extra_links.forEach(({url, config: {link_class, new_tab, link_text}}) => {
            $("ul.breadcrumb").append(
                `<li>
                    <span class="divider">|</span>
                    <a href="${url}" class="btn ${link_class}" target="${new_tab ? '_blank' : ''}">${link_text}</a>
                </li>`
            )
        });
    },
    initChangeForm: function (data) {
        if (data.hide_save_buttons) {
            $(".submit-row").remove();
        } else {
            data.extra_submit_buttons.forEach(({name, config: {btn_text, btn_class}}) => {
                $(".submit-row").append(
                    `<button name="__${name}" type="submit" class="btn ${btn_class}">${btn_text}</button>`
                )
            });
        }
    }
};

$(document).ready(function () {
    if ($("#changelist").size() || $("body").hasClass("change-form")) {
        EnhancedAdminMixin.init();
    }
});