import express, { Request, Response } from "express";
import apiRoutes from "./routes/apiRoutes";

const app = express();
const PORT: number = 8000;

app.use(express.json());
app.use("/", apiRoutes);

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});