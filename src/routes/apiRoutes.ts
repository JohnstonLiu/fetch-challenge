import { Router, Request, Response } from "express";
import { Heap } from "heap-js";
import moment from "moment";

const router: Router = Router();

interface Txn {
  payer: string;
  points: number;
  timestamp: EpochTimeStamp;
}

var payers: Map<string, number> = new Map(); 
const txnTimeComparator = (a: Txn, b: Txn) => a.timestamp - b.timestamp;
var txnHist: Heap<Txn> = new Heap(txnTimeComparator);

// POST /add
router.post("/add", (req: Request, res: Response) => {
  var base: number = payers.get(req.body.payer) ?? 0;
  payers.set(req.body.payer, base + req.body.points);
  const newTxn: Txn = {
    payer: req.body.payer,
    points: req.body.points,
    timestamp: moment.utc(req.body.timestamp).unix()
  };
  txnHist.push(newTxn);
  res.status(200).send();
});

/**
 * Generates a map representing the "difference" of two maps (<string, number>).
 * Assumes both maps have identical key sets.
 *
 * @param a - Subtracted map
 * @param b - Map to subtract from
 * @returns map representing "b - a"
 */
function compPayerDelta(a: Map<string, number>, b: Map<string, number>): Map<string, number> {
  const delta: Map<string, number> = new Map(b);
  delta.forEach((val, key) => {
    delta.set(key, val-a.get(key)!)
  });
  return delta;
}

interface spendResponseElement {
  payer: string;
  points: number;
}

/**
 * Formats a <string, number> map into the corresponding JSON object for our POST /spend response.
 *
 * @param map - Hashmap to be formatted
 * @returns Formatted JSON object
 */
function spendResponseFormat(map: Map<string, number>): spendResponseElement[] {
  const response: spendResponseElement[] = [];
  map.forEach((val, key) => {
    const obj: spendResponseElement = {
      payer: key,
      points: val
    };
    response.push(obj);
  });
  return response;
}

/**
 * Generates array of transactions from txnHist heap. Then normalizes the array
 * and returns it.
 * 
 * @returns Array of normalized transactions order-preserved from txnHist heap.
 */
function getNormalizedTxns(): Txn[] {
  const txns: Txn[] = [];
  for (const txn of txnHist.clone()) {
    txns.push(txn);
  }
  for (var i = 1; i < txns.length; ++i) {
    if (txns[i].points >= 0) {
      continue;
    }
    for (var j = i-1; j >= 0; --j) {
      if (txns[j].payer !== txns[i].payer) {
        continue;
      }
      const deduct: number = Math.min(txns[j].points, -txns[i].points);
      txns[j].points -= deduct;
      txns[i].points += deduct;
      if (txns[i].points == 0) {
        break;
      }
    }
  }
  return txns;
}

// POST /spend
router.post("/spend", (req: Request, res: Response) => {
  var points: number = req.body.points;
  const heap: Heap<Txn> = new Heap(txnTimeComparator);
  heap.init(getNormalizedTxns());
  const newPayers: Map<string, number> = new Map(payers);

  while (!heap.isEmpty() && points > 0) {
    const txn: Txn = heap.pop()!;
    if (txn.points == 0) {
      continue;
    }
    const deduct: number = Math.min(points, txn.points); 
    points -= deduct;
    txn.points -= deduct;
    if (txn.points > 0) {
      heap.push(txn);
    }
    const base: number = newPayers.get(txn.payer) ?? 0;
    newPayers.set(txn.payer, base - deduct);
  }

  if (points == 0) {
    const resMap: Map<string, number> = compPayerDelta(payers, newPayers);
    res.status(200).json(spendResponseFormat(resMap));
    txnHist = heap;
    payers = newPayers;
    return;
  }
  res.status(400).send(`Failed to spend ${req.body.points} points. The user does not have enough points`);
});

// GET /balance
router.get("/balance", (req: Request, res: Response) => {
  res.status(200).json(Object.fromEntries(payers));
});

export default router;