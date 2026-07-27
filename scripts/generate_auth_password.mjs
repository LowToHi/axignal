import { randomBytes, scryptSync } from "node:crypto";

const password = process.argv[2];
if (!password || password.length < 12) {
  console.error("Usage: node scripts/generate_auth_password.mjs '<password-with-12-or-more-characters>'");
  process.exit(1);
}

const salt = randomBytes(16);
const derived = scryptSync(password, salt, 32);
console.log(`scrypt$${salt.toString("hex")}$${derived.toString("hex")}`);
