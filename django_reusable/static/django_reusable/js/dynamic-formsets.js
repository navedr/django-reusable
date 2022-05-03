const formClassName = '.dynamic-form-row';
const formsContainer = '.formset-forms';
const addBtnClassName = '.add-form-row';
const removeBtnClassName = '.remove-form-row';
const prefixAttrs = ['name', 'id', 'for'];
const serialNoClassName = '.serial-no';
const emptyFormDataAttr = '[data-empty-form]';

(function ($) {

    $.fn.extend({
        dynamicFormSet: function (options) {
            options = $.extend({}, $.DynamicFormSet.defaults, options);

            this.each(function () {
                new $.DynamicFormSet(this, options);
            });

            return this;
        }
    });

    // ctl is the element, options is the set of defaults + user options
    $.DynamicFormSet = function (ctl, options) {
        const $el = $(ctl);
        const $total = $(`#id_${options.prefix}-TOTAL_FORMS`);

        function bindEvents() {
            $($el).on('click', addBtnClassName, function (e) {
                e.preventDefault();
                const total = parseInt($total.val());
                if (total < options.maxNum) {
                    addForm();
                }
                e.stopPropagation();
                return false;
            });

            $($el).on('click', removeBtnClassName, function (e) {
                e.preventDefault();
                deleteForm($(this));
                e.stopPropagation();
                return false;
            });
            toggleAddButton();
            limitDeleteButtons();
        }

        function updateElementIndex(el, ndx) {
            const id_regex = new RegExp('(' + options.prefix + '-\\d+)');
            const replacement = options.prefix + '-' + ndx;
            if ($(el).attr("for")) $(el).attr("for", $(el).attr("for").replace(id_regex, replacement));
            if (el.id) el.id = el.id.replace(id_regex, replacement);
            if (el.name) el.name = el.name.replace(id_regex, replacement);
        }

        function addForm() {
            const $form = $($el.find(emptyFormDataAttr).html().replace("<\\/script>", "</script>"));
            updatedPrefixes($form);
            $total.val(parseInt($total.val()) + 1);
            $el.find(formsContainer).append($form);
            toggleAddButton();
            updateSerialNo();
            limitDeleteButtons();
            return false;
        }

        function updatedPrefixes($form) {
            const total = $total.val();
            const prefixSelector = prefixAttrs.map(attr => `[${attr}*="__prefix__"]`).join(', ');
            const $prefixEl = $form.find(prefixSelector);
            $prefixEl.each((i, el) => {
                const $pe = $(el);
                prefixAttrs.forEach(attr => {
                    const value = $pe.attr(attr);
                    if (value && value.match('__prefix__')) {
                        $pe.attr(attr, value.replace('__prefix__', total));
                    }
                });
            });
            $form.html($form.html().replace('__prefix__', total))
        }

        function deleteForm(btn) {
            const total = parseInt($total.val());
            if (total > options.minNum) {
                btn.closest(formClassName).remove();
                const $forms = $el.find(formClassName);
                $total.val($forms.length);
                for (let i = 0, formCount = $forms.length; i < formCount; i++) {
                    $($forms.get(i)).find(':input').each(function () {
                        updateElementIndex(this, i);
                    });
                }
            }
            toggleAddButton();
            updateSerialNo();
            limitDeleteButtons();
            return false;
        }

        function toggleAddButton() {
            const total = parseInt($total.val());
            $el.find(addBtnClassName).toggleClass('hide', total === options.maxNum);
        }

        function updateSerialNo() {
            $.each($el.find(formClassName), (i, el) => {
                $(el).find(serialNoClassName).html(`# ${i + 1}`);
            });
        }

        function limitDeleteButtons() {
            if (options.minNum) {
                $.each($el.find(formClassName), (i, el) => {
                    if (i < options.minNum) {
                        $(el).find(removeBtnClassName).remove();
                    }
                });
            }
        }

        bindEvents();
        return this;
    };

    // option defaults
    $.DynamicFormSet.defaults = {
        prefix: 'form',
        minNum: undefined,
        maxNum: undefined,
        canDelete: true
    };

})(jQuery);