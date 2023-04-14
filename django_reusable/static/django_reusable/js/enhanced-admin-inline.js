const EnhancedAdminInline = {
    select2Inlines: [],
    init: function () {
        this.initInlineSelect2();
    },
    initInlineSelect2: function () {
        if (Suit.$.fn.select2) {
            $.each($(".dr-inline-select2"), $.proxy(this.convertInlineSelectToSelect2, this));
            $(document).bind("DOMNodeInserted", $.proxy(this.onDomNodeInserted, this));
        }
    },
    onDomNodeInserted: function (event) {
        const $newForm = Suit.$(event.target);

        // form-row for tabular inline and inline-related for stacked inline
        if (!$newForm.hasClass("form-row") && !$newForm.hasClass("inline-related")) {
            return;
        }

        this.select2Inlines
            .filter(({ newFormClass }) => $newForm.hasClass(newFormClass))
            .forEach(({ parentClass, options }) =>
                $newForm.find(`.${parentClass} select:visible:not(.select2-offscreen)`).select2({
                    width: "resolve",
                    ajax: {
                        transport: function (params, success, failure) {
                            let results = options;
                            if (params.data.q) {
                                results = results.filter(item =>
                                    item.text.toLowerCase().match(params.data.q.toLowerCase()),
                                );
                            }
                            success({ results });
                        },
                    },
                }),
            );
    },
    convertInlineSelectToSelect2: function (i, el) {
        const $select = Suit.$(el);
        if ($select.parents(".empty-form").size()) {
            // td for tabular inline and control-group for stacked inline
            const parentClass = $select
                    .parents("td, .control-group")
                    .attr("class")
                    .split(" ")
                    .find(c => c.match("field-")),
                $emptyForm = $select.parents(".empty-form"),
                newFormClass = "dynamic-" + $emptyForm.attr("id").replace("-empty", "");
            const options = $select
                .find("option")
                .map((i, option) => ({
                    id: $(option).attr("value"),
                    text: $(option).text(),
                }))
                .toArray();
            $select.empty();
            this.select2Inlines.push({ newFormClass, parentClass, options });
        } else {
            $select.select2({ width: "resolve" });
        }
    },
};

$(document).ready(function () {
    EnhancedAdminInline.init();
});
