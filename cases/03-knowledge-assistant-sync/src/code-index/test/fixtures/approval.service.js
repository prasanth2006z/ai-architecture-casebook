const db = require('../db');
const pool = require('../pool');
const { ClaimStatus } = require('../domain/claimStatus');

/** Approve some items of a claim and reject the rest (CLM-482). */
async function approvePartial(claimId, decisions) {
  const claim = await db('claims').where({ claim_id: claimId }).first();
  for (const d of decisions) {
    await db('claim_items').where({ item_id: d.itemId })
      .update({ approved_amount: d.amount });
  }
  await db('claims').where({ claim_id: claimId })
    .update({ status: ClaimStatus.PARTIALLY_APPROVED });
  return { ok: true, claimId: claim.claim_id };
}

const getClaim = async (req, res) => {
  const { rows } = await pool.query(
    `SELECT c.*, s.changed_at FROM claims c
     JOIN claim_status_history s ON s.claim_id = c.claim_id
     WHERE c.claim_id = $1`, [req.params.id]);
  res.json(rows[0]);
};

const isFinal = (s) => s === 'PAID' || s === 'REJECTED';

module.exports = { approvePartial, getClaim, isFinal };
