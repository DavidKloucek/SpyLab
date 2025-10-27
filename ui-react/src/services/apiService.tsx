import { useCustom } from "@refinedev/core";
import axiosClient from "./apiClient";
import { DashStats, getDashboardApiDashboardGetUrl, getUserListApiUsersGetUrl } from "../api/generated";

export const useDashboardStats = () => {
    return useCustom<DashStats>({
        url: getDashboardApiDashboardGetUrl(),
        method: "get",
    })
}

export const useUsersNoProvider = (offset: number, limit: number) => {
    return axiosClient.get(getUserListApiUsersGetUrl({
        _start: offset,
        _end: limit
    }));
}
