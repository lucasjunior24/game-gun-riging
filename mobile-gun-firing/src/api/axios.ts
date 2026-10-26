import axios from "axios";

const api = axios.create({
    baseURL: "http://192.168.100.135:9000",
    // baseURL: "http://localhost:9000",
    // Sem timeout, um IP errado deixa a tela presa em "Carregando partida..."
    timeout: 10000,
    headers: {
        // Authorization: `Bearer Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJpbmciLCJzY29wZXMiOltdLCJleHAiOjE3NTY1OTIxNzl9.madSvE3cNcI3cOO-qyrDRXr-gr4SGK-Iu3GIv_AHHEg`,
        Authorization: `Bearer Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJpbmciLCJzY29wZXMiOltdLCJleHAiOjE3ODI0MzUzODV9.7tSNzF0O9hs0grPsp4MS-A_LMP1qWlHb5Ru4nfxKNrU`,
        "Content-Type": "application/json",
        accept: "application/json",
    },
});
export { api };
