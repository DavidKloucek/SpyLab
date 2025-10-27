import axios, {
    AxiosError,
    AxiosHeaders,
    AxiosRequestConfig,
    InternalAxiosRequestConfig,
} from "axios";
import { jwtDecode } from "jwt-decode";

type TAccess = { token: string; exp: number };

type AuthConfig = InternalAxiosRequestConfig & { _skipAuth?: boolean };
type RetryConfig = AxiosRequestConfig & { _skipAuth?: boolean };

let access: TAccess | null = null;
let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

export function getAccessToken(): TAccess | null {
    return access;
}
export function setAccessToken(info: TAccess | null) {
    access = info;
}

export const apiUrl = "http://localhost:8000"
export const resourceApiUrl = apiUrl + "/api"

const axiosClient = axios.create({
    baseURL: apiUrl,
    withCredentials: true,
});

const axiosRefresh = axios.create({
    baseURL: apiUrl,
    withCredentials: true,
});

function isAccessTokenExpired(): boolean {
    const exp = getAccessToken()?.exp;
    if (!exp) return true;
    return Date.now() / 1000 > Number(exp) - 60;
}

function setAuthHeaderOnConfig(
    cfg: Pick<AxiosRequestConfig, "headers">,
    token: string
): void {
    if (cfg.headers instanceof AxiosHeaders) {
        cfg.headers.set("Authorization", `Bearer ${token}`);
    } else {
        cfg.headers = { ...(cfg.headers || {}), Authorization: `Bearer ${token}` };
    }
}

async function ensureRefreshed(): Promise<void> {
    if (isRefreshing && refreshPromise) {
        await refreshPromise;
        return;
    }
    isRefreshing = true;
    refreshPromise = axiosRefresh.post("/auth/refresh", {}).then((resp) => {
        const at = resp.data?.token as string | undefined;
        const expiresIn = Number(jwtDecode(resp.data?.token).exp);
        if (!at || !expiresIn) {
            throw new Error("Refresh response missing access_token or expires_in");
        }
        setAccessToken({
            token: at,
            exp: Math.floor(Date.now() / 1000) + expiresIn,
        });
    }).finally(() => {
        isRefreshing = false;
    });

    await refreshPromise;
}

axiosClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const apiMessage = error?.response?.data?.message;
        if (apiMessage) {
            error.message = apiMessage;
        }
        console.log("error", error)
        error.statusCode = error?.status
        return Promise.reject(error);
    }
);

axiosClient.interceptors.request.use(async (config: AuthConfig) => {
    const url = config.url ?? "";

    if (config._skipAuth || url.includes("/auth/refresh")) {
        return config;
    }

    const token = getAccessToken()?.token;
    if (token && isAccessTokenExpired()) {
        //await ensureRefreshed();
    }

    const finalToken = getAccessToken()?.token;
    if (finalToken) {
        setAuthHeaderOnConfig(config, finalToken);
    }

    return config;
});

axiosClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        const cfg = error.config as RetryConfig | undefined;

        if (
            error.response?.status === 401 &&
            cfg &&
            !cfg._skipAuth &&
            !(cfg.url ?? "").includes("/auth/refresh") &&
            !(cfg.url ?? "").includes("/auth")
        ) {
            try {
                //await ensureRefreshed();

                const newToken = getAccessToken()?.token;
                const retryCfg: RetryConfig = { ...cfg, _skipAuth: true };
                if (newToken) {
                    setAuthHeaderOnConfig(retryCfg, newToken);
                }

                return axiosClient.request(retryCfg);
            } catch {
                setAccessToken(null);
            }
        }

        return Promise.reject(error);
    }
);

export default axiosClient;
