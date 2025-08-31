import axios from "axios";

const api = axios.create({
    baseURL: "http://192.168.100.37:9000",
    // baseURL: "http://localhost:9000",
    headers: {
        Authorization: `Bearer Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJpbmciLCJzY29wZXMiOltdLCJleHAiOjE3NTY1OTIxNzl9.madSvE3cNcI3cOO-qyrDRXr-gr4SGK-Iu3GIv_AHHEg`,
        "Content-Type": "application/json",
        accept: "application/json",
    },
});
export { api };
