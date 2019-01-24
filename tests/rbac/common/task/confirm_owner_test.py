# Copyright 2019 Contributors to Hyperledger Sawtooth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -----------------------------------------------------------------------------
"""Confirm Task Add Owner Test"""
# pylint: disable=no-member,too-many-locals

import logging
import pytest

from rbac.common import rbac
from rbac.common import protobuf
from tests.rbac.common import helper

LOGGER = logging.getLogger(__name__)


@pytest.mark.task
@pytest.mark.library
def test_make():
    """Test making the message"""
    related_id = helper.user.id()
    object_id = helper.task.id()
    proposal_id = helper.proposal.id()
    reason = helper.proposal.reason()
    message = rbac.task.owner.confirm.make(
        proposal_id=proposal_id,
        related_id=related_id,
        object_id=object_id,
        reason=reason,
    )
    assert isinstance(message, protobuf.proposal_transaction_pb2.UpdateProposal)
    assert message.proposal_id == proposal_id
    assert message.related_id == related_id
    assert message.object_id == object_id
    assert message.reason == reason


@pytest.mark.task
@pytest.mark.library
def test_make_addresses():
    """Test making the message addresses"""
    related_id = helper.user.id()
    object_id = helper.task.id()
    proposal_id = helper.proposal.id()
    proposal_address = rbac.task.owner.propose.address(object_id, related_id)
    reason = helper.proposal.reason()
    relationship_address = rbac.task.owner.address(object_id, related_id)
    signer_user_id = helper.user.id()
    helper.user.key()

    user_address = rbac.user.address(related_id)
    signer_admin_address = rbac.task.admin.address(object_id, signer_user_id)
    signer_owner_address = rbac.task.owner.address(object_id, signer_user_id)
    message = rbac.task.owner.confirm.make(
        proposal_id=proposal_id,
        related_id=related_id,
        object_id=object_id,
        reason=reason,
    )

    inputs, outputs = rbac.task.owner.confirm.make_addresses(
        message=message, signer_user_id=signer_user_id
    )

    assert user_address in inputs
    assert signer_admin_address in inputs
    assert signer_owner_address in inputs
    assert proposal_address in inputs
    assert relationship_address in inputs

    assert proposal_address in outputs
    assert relationship_address in outputs


@pytest.mark.task
@pytest.mark.confirm_task_owner
def test_create():
    """Test executing the message on the blockchain"""
    proposal, _, task_owner, task_owner_key, _, _ = helper.task.owner.propose.create()

    reason = helper.task.owner.propose.reason()
    message = rbac.task.owner.confirm.make(
        proposal_id=proposal.proposal_id,
        object_id=proposal.object_id,
        related_id=proposal.related_id,
        reason=reason,
    )

    status = rbac.task.owner.confirm.new(
        signer_keypair=task_owner_key,
        signer_user_id=task_owner.user_id,
        message=message,
    )

    assert len(status) == 1
    assert status[0]["status"] == "COMMITTED"

    confirm = rbac.task.owner.confirm.get(
        object_id=proposal.object_id, related_id=proposal.related_id
    )

    assert isinstance(confirm, protobuf.proposal_state_pb2.Proposal)
    assert confirm.proposal_type == protobuf.proposal_state_pb2.Proposal.ADD_TASK_OWNER
    assert confirm.proposal_id == proposal.proposal_id
    assert confirm.object_id == proposal.object_id
    assert confirm.related_id == proposal.related_id
    assert confirm.close_reason == reason
    assert confirm.closer == task_owner.user_id
    assert confirm.status == protobuf.proposal_state_pb2.Proposal.CONFIRMED
    assert rbac.task.owner.exists(
        object_id=proposal.object_id, related_id=proposal.related_id
    )
