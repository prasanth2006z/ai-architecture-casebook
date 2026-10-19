const express = require('express');
const router = express.Router();
const { requireRole } = require('../middleware/auth');
const approval = require('../services/approval.service');

/** Partial approval of a claim (CLM-482). */
router.post('/claims/:id/approve-partial', requireRole('adjuster'), async (req, res) => {
  const result = await approval.approvePartial(req.params.id, req.body.decisions);
  res.status(200).json(result);
});

router.get('/claims/:id', approval.getClaim);

module.exports = router;
