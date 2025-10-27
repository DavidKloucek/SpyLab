import { Skeleton } from "antd"
import { Card, Row, Col, Statistic, Tooltip, Tag, Typography, Space } from "antd";
import { UserOutlined } from "@ant-design/icons";
import { useDashboardStats } from "../../services/apiService";
const { Title, Text } = Typography;

export const Home = () => {

    const { query, result } = useDashboardStats()

    return <>
        <div>
            <Card title="Dashboard">

                <Title level={3} style={{ marginBottom: 16 }}>Statistics</Title>

                {query.isLoading || !result.data ? (
                    <Skeleton active paragraph={{ rows: 2 }} />
                ) : (
                    <Row gutter={[16, 16]}>
                        <Col xs={24} sm={12} md={8}>
                            <StatBubble
                                title={
                                    null
                                }
                                value={query.data?.data.face_count_total ?? 0}
                                icon={<UserOutlined />}
                                tooltip="Total number of all stored embeddings in the database"
                                color="#1677ff"
                                bg="linear-gradient(135deg, rgba(22,119,255,0.18), rgba(22,119,255,0.06))"
                                trend={
                                    <Tag color={(query.data?.data.face_count_24h ?? 0) > 0 ? "green" : undefined} style={{ borderRadius: 999 }}>
                                        +<strong>{query.data?.data.face_count_24h ?? 0}</strong> in the last 24 hours
                                    </Tag>
                                }
                            />
                        </Col>
                    </Row>
                )}
            </Card>
        </div>
    </>
}

function StatBubble({
    title,
    value,
    suffix,
    icon,
    tooltip,
    color = "#1677ff",
    bg = "linear-gradient(135deg, rgba(22,119,255,0.15), rgba(22,119,255,0.05))",
    footer,
    trend,
}: {
    title: React.ReactNode;
    value: number | string;
    suffix?: string;
    icon?: React.ReactNode;
    tooltip?: React.ReactNode;
    color?: string;
    bg?: string;
    footer?: React.ReactNode;
    trend?: React.ReactNode | string | null;
}) {
    return (
        <Tooltip title={tooltip} placement="top">
            <Card
                variant="outlined"
                style={{
                    borderRadius: 24,
                    background: bg,
                    boxShadow: "0 8px 24px rgba(0,0,0,0.06)",
                }}
                styles={{ body: { padding: 18 } }}
            >
                <Space align="start" style={{ width: "100%" }}>
                    <div
                        style={{
                            width: 58,
                            height: 58,
                            borderRadius: 999,
                            background: color,
                            display: "grid",
                            placeItems: "center",
                            boxShadow: "0 8px 18px rgba(0,0,0,0.12)",
                            flex: "0 0 58px",
                        }}
                    >
                        <div style={{ color: "#fff", fontSize: 26 }}>{icon}</div>
                    </div>
                    <div style={{ flex: 1 }}>
                        <Text type="secondary" style={{ fontSize: 13 }}>{title}</Text>
                        <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 4 }}>
                            <Statistic value={value as any} suffix={suffix} valueStyle={{ fontWeight: 800, fontSize: 28, lineHeight: 1 }} />
                            {trend ? trend : null}
                        </div>
                        {footer && <div style={{ marginTop: 8 }}>{footer}</div>}
                    </div>
                </Space>
            </Card>
        </Tooltip>
    );
}
