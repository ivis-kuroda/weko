# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import enum
import json
import re

from invenio_db import db
from flask import current_app
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy_utils.types import JSONType

from invenio_oauth2server.models import Client
from weko_records.models import ItemType, Timestamp
from weko_workflow.models import WorkFlow

"""swordserver models."""


class SwordItemTypeMapping(db.Model, Timestamp):
    """SwordItemTypeMapping Model

    Mapping of RO-Crate matadata to WEKO item type.

    Columns:
        `id` (int): ID of the mapping.
        `name` (str): Name of the mapping.
        `mapping` (JSON): Mapping in JSON format.
        `itemtype_id` (str): Target itemtype of the mapping.\
            Foreign key referencing `ItemType.id`.
        `version_id` (int): Version ID of the mapping.
        `is_deleted` (bool): Sofr-delete status of the mapping.
    """

    __tablename__ = 'sword_item_type_mappings'

    id = db.Column(db.Integer, primary_key=True, unique=True)
    """ID of the mapping."""

    name = db.Column(db.String(255), nullable=False)
    """Name of the mapping."""

    mapping = db.Column(
        db.JSON().with_variant(
            postgresql.JSONB(none_as_null=True),
            'postgresql',
        ).with_variant(
            JSONType(),
            'sqlite',
        ).with_variant(
            JSONType(),
            'mysql',
        ),
        default=lambda: {},
        nullable=False
    )
    """Mapping in JSON format. Foreign key of ItemType."""

    itemtype_id = db.Column(
        db.Integer(),
        db.ForeignKey(ItemType.id),
        nullable=False)
    """Target itemtype of the mapping."""

    version_id = db.Column(db.Integer, primary_key=True)
    """Version id of the mapping."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Sofr-delete status of the mapping."""

    # __mapper_args__ = {
    #     'version_id_col': version_id
    # }

    @classmethod
    def get_object_by_id(cls, mapping_id, ignore_deleted=False):
        """Get mapping by mapping_id.

        Args:
            mapping_id (int): Mapping ID.
            ignore_deleted (bool, optional): Ignore deleted mapping.

        Returns:
            SwordItemTypeMapping:
            Mapping object. If not found or deleted, return `None`.
        """

        obj = (
            cls.query
            .filter_by(id=mapping_id)
            .order_by(cls.version_id.desc())
            .first()
        )

        if not ignore_deleted and obj and obj.is_deleted:
            return None
        return obj

    @classmethod
    def get_object_by_id_all_versions(cls, mapping_id):
        """Get mapping by mapping_id.

        Args:
            mapping_id (int): Mapping ID.

        Returns:
            list: Mapping object. if not found, return empty list.
        """

        obj = (
            cls.query
            .filter_by(id=mapping_id)
            .order_by(cls.version_id.desc())
            .all()
        )

        return obj

    @classmethod
    def get_mapping_by_id(cls, mapping_id, ignore_deleted=False):
        """Get mapping by mapping_id.

        Args:
            mapping_id (int): Mapping ID.
            ignore_deleted (bool, optional): Ignore deleted mapping.

        Returns:
            dict: Mapping in JSON format.
            If not found or deleted, return `None`.
        """

        obj = cls.get_object_by_id(mapping_id, ignore_deleted)
        if obj is None:
            return None
        return obj.mapping

    @classmethod
    def _get_next_id(cls):
        """Get next mapping id.

        Returns:
            int: Next new mapping id.
        """
        return cls.query.count() + 1

    @classmethod
    def create(cls, name, mapping, itemtype_id):
        """Create mapping.

        Args:
            name (str): Name of the mapping.
            mapping (dict): Mapping in JSON format.
            itemtype_id (str): Target itemtype of the mapping.

        Returns:
            SwordItemTypeMapping: Created mapping object.
        """
        obj = cls(
            id=cls._get_next_id(),
            name=name,
            mapping=mapping,
            itemtype_id=itemtype_id,
            version_id=1,
            is_deleted=False
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def update(cls, id, name=None, mapping=None, itemtype_id=None):
        """Update mapping.

        Args:
            id (int): Mapping ID.
            name (str): Name of the mapping.
            mapping (dict): Mapping in JSON format.
            itemtype_id (str): Target itemtype of the mapping.

        Returns:
            SwordItemTypeMapping: Updated mapping object.
        """
        obj = cls.get_object_by_id(id)
        if obj is None:
            return None

        obj.is_deleted = True

        new_obj = cls(
            id=obj.id,
            name=name or obj.name,
            mapping=mapping or obj.mapping,
            itemtype_id=itemtype_id or obj.itemtype_id,
            version_id=obj.version_id + 1,
            is_deleted=False
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
                db.session.add(new_obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj


class SwordClient(db.Model, Timestamp):
    """SwordClient Model

    client whitch is register items through the sword api.

    Columns:
        `client_id` (str): ID of the client.\
            Foreign key referencing `Client.client_id`.
        `registration_type` (int): Type of registration to register an item.
        `mapping_id` (int): Mapping ID of the client.\
            Foreign key referencing `SwordItemTypeMapping.id`.
        `workflow_id` (int, optional): Workflow ID of the client.\
            Foreign key referencing `WorkFlow.id`.
        `is_deleted` (bool): Sofr-delete status of the client.

    Nested Classes:
        `RegistrationType` (enum.IntEnum): Enum class for registration type.
            - `Direct` (1): Direct registration.
            - `Workfolw` (2): Workflow registration.
    """

    class RegistrationType(enum.IntEnum):
        """Solution to register item."""

        Direct = 1
        Workfolw = 2

    __tablename__ = 'sword_clients'

    client_id = db.Column(
        db.String(255),
        db.ForeignKey(Client.client_id),
        primary_key=True,
        unique=True)
    """Id of the clients. foreign key of Client."""

    registration_type = db.Column(
        db.SmallInteger, unique=False, nullable=False)
    """Type of registration to register an item."""

    mapping_id = db.Column(
        db.Integer,
        db.ForeignKey(SwordItemTypeMapping.id),
        unique=False,
        nullable=False)
    """Mapping ID of the client. foreign key of SwordItemTypeMapping."""

    workflow_id = db.Column(
        db.Integer,
        db.ForeignKey(WorkFlow.id),
        unique=False,
        nullable=True)
    """Workflow ID of the client. foreign key of WorkFlow."""

    is_deleted = db.Column(
        db.Boolean(name='is_deleted'),
        nullable=False,
        default=False)
    """Sofr-delete status of the client."""

    @classmethod
    def get_client_by_id(cls, client_id, ignore_deleted=False):
        """Get client by client_id.

        Args:
            client_id (str): Client ID.
            ignore_deleted (bool, optional): Ignore deleted client.

        Returns:
            SwordClient: Client object.
        """
        obj = cls.query.filter_by(client_id=client_id).one_or_none()
        if not ignore_deleted and obj and obj.is_deleted:
            return None
        return obj

    @classmethod
    def get_mapping_by_client_id(cls, client_id, ignore_deleted=False):
        obj = (
            cls.query
            .join(SwordItemTypeMapping, cls.mapping_id == SwordItemTypeMapping.id)
            .filter(cls.client_id == client_id)
            .order_by(SwordItemTypeMapping.version_id.desc())
            .first()
        )

        if not ignore_deleted and obj and obj.is_deleted:
            return None
        return json.loads(obj.mapping)

    @classmethod
    def create(cls, client_id, registration_type, mapping_id,
                workflow_id, is_deleted=False):
        """Create client.

        Args:
            client_id (str): Client ID.
            registration_type (int): Type of registration.
            mapping_id (int): Mapping ID.
            workflow_id (int): Workflow ID.
            is_deleted (bool, optional): Soft-delete status.

        Returns:
            SwordClient: Client object.
        """
        obj = cls(
            client_id=client_id,
            registration_type=registration_type,
            mapping_id=mapping_id,
            workflow_id=workflow_id,
            is_deleted=is_deleted
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def update(cls, client_id, registration_type=None, mapping_id=None,
               workflow_id=None, is_deleted=None):
        """Update client.

        Args:
            client_id (str): Client ID.
            registration_type (int): Type of registration.
            mapping_id (int): Mapping ID.
            workflow_id (int): Workflow ID.
            is_deleted (bool, optional): Soft-delete status.

        Returns:
            SwordClient: Client object.
        """
        obj = cls.get_client_by_id(client_id)
        if obj is None:
            return None

        obj.registration_type = registration_type or obj.registration_type
        obj.mapping_id = mapping_id or obj.mapping_id
        obj.workflow_id = workflow_id or obj.workflow_id
        obj.is_deleted = is_deleted or obj.is_deleted

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj

    @classmethod
    def delete(cls, client_id):
        """Soft-delete client.

        Args:
            client_id (str): Client ID.

        Returns:
            SwordClient: Client object.
        """
        obj = cls.get_client_by_id(client_id)
        if obj is None:
            return None

        obj.is_deleted = True

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            current_app.logger.error(ex)
            db.session.rollback()
            raise

        return obj
