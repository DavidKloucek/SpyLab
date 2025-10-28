import axiosClient from "../services/apiClient";

import type { AxiosRequestConfig } from 'axios';

export const orvalMutator = async <T>(
    { url, method, params, data, headers }: AxiosRequestConfig
): Promise<T> => {
    const response = await axiosClient({
        url,
        method,
        params,
        data,
        headers,
    });
    return response.data as T;
};