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
        this.loadLazyListFields(data.lazy_list_fields || []);
    },
    initChangeForm: function (data) {
        if (data.hide_save_buttons) {
            $(".submit-row").remove();
        } else {
            data.extra_submit_buttons.forEach(({name, config: {btn_text, btn_class, confirm}}) => {
                const $button = $(`<button name="__${name}" type="submit" class="btn ${btn_class}">${btn_text}</button>`);
                if (confirm) {
                    $button.attr("onclick", `return confirm('${confirm}');`);
                }
                $(".submit-row").append($button);
            });
        }
        this.loadLazyFields(data.lazy_load_fields || []);
    },
    loadLazyListFields: function (fields) {
        fields.forEach(function (fieldName) {
            var $spans = $('span.dr-lazy-list[data-field="' + fieldName + '"]');
            if (!$spans.length) return;
            var pks = [];
            $spans.each(function () { pks.push($(this).data("pk")); });
            var url = location.pathname + "dr-lazy-list-field/" + fieldName + "/";
            fetch(url, {
                method: "POST",
                headers: {"Content-Type": "application/json", "X-CSRFToken": $("[name=csrfmiddlewaretoken]").val()},
                body: JSON.stringify({pks: pks})
            }).then(function (r) { return r.json(); }).then(function (data) {
                $spans.each(function () {
                    var pk = String($(this).data("pk"));
                    if (data[pk] !== undefined) {
                        $(this).replaceWith(data[pk]);
                    }
                });
            }).catch(function () {
                $spans.html('<span style="color:red">Failed</span>');
            });
        });
    },
    loadLazyFields: function (fields) {
        fields.forEach(function (fieldName) {
            var $container = $(".field-" + fieldName + " .readonly");
            if (!$container.length) {
                $container = $(".field-" + fieldName + " div > p");
            }
            if (!$container.length) return;
            var url = location.pathname + "dr-lazy-field/" + fieldName + "/";
            $container.html('<span style="color:#999">Loading...</span>');
            fetch(url).then(function (r) { return r.text(); }).then(function (html) {
                $container.html(html);
            }).catch(function () {
                $container.html('<span style="color:red">Failed to load</span>');
            });
        });
    },
    handleAjaxFields: function () {
        $(".dr-ajax-action-btn").click(function (e) {
            const confirm_text = $(e.currentTarget).data("confirm");
            if (confirm_text) {
                if (!confirm(confirm_text)) {
                    return false;
                }
            }
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
