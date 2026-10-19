import { Pool } from 'pg';
import { audit } from './audit';

/** Handles claim rejections. */
export class RejectionService {
  constructor(private readonly pool: Pool) {}

  async reject(claimId: string, reason: string): Promise<void> {
    await this.pool.query("UPDATE claims SET status = 'REJECTED' WHERE claim_id = $1", [claimId]);
    await audit.log(claimId, reason);
    // reason is free text from the adjuster
  }

  get name(): string { return 'rejection'; }
}
