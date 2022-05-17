

def remove_from_fieldsets(fieldsets, fields):
    if not fields:
        return
    for fieldset in fieldsets:
        flattened_fields = []
        for field in fieldset[1]['fields']:
            if isinstance(field, str):
                flattened_fields.append(field)
            elif isinstance(field, tuple):
                flattened_fields.extend(list(field))
        for field in fields:
            if field in flattened_fields:
                new_fields = []
                for new_field in fieldset[1]['fields']:
                    if isinstance(new_field, str):
                        if new_field not in fields:
                            new_fields.append(new_field)
                    elif isinstance(new_field, tuple):
                        new_field_tuple = []
                        for f in list(new_field):
                            if f not in fields:
                                new_field_tuple.append(f)
                        if new_field_tuple:
                            new_fields.append(tuple(new_field_tuple))
                fieldset[1]['fields'] = tuple(new_fields)
                break
