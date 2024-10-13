# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


from weko_swordserver.models import SwordItemTypeMapping, SwordClient

class TestSwordItemTypeMapping():
    # .tox/c1/bin/pytest --cov=weko_swordserver tests/test_models.py::TestSwordItemTypeMapping::test_get_object_by_id -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
    def test_get_object_by_id(app, db, item_type):
        obj = SwordItemTypeMapping(
            id=1,
            name="test",
            mapping={"test": "test"},
            itemtype_id=item_type["item_type"].id,
            version_id=1,
            is_deleted=False
        )

        with db.session.begin_nested():
            db.session.add(obj)
        db.session.commit()

        assert SwordItemTypeMapping.get_object_by_id(obj.id) == obj
