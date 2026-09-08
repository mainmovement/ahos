import "dotenv/config";
import { seedCli } from "@/db/seed";

seedCli()
  .then(() => process.exit(0))
  .catch((e) => {
    console.error(e);
    process.exit(1);
  });
