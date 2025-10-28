import { useCustom, } from "@refinedev/core";
import { DashStats, getSpyLab } from "../api/generated";

export const useDashboardStats = () => {
    return useCustom<DashStats>({
        method: "get",
        url: "/api/dashboard"
    });
};

export const useUsersNoProviderExample = (offset: number, limit: number) => {
    return getSpyLab().userListApiUsersGet({
        _start: offset,
        _end: limit
    })
}
