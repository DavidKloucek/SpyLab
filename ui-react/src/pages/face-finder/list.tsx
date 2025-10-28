import {
    List,
    useModal,
    useTable,
} from "@refinedev/antd";
import { useCustomMutation } from "@refinedev/core";
import { Modal, Table, Tooltip } from "antd";
import { FaceBox, FacePicker } from "../../components/FacePicker";
import { useEffect, useState } from "react";
import { FaceSearchPanel } from "../../components/FaceSearchPanel";
import { FaceSimilarItemResponse } from "../../api/generated";

export const FaceFinderList = () => {

    const { tableProps, } = useTable({
        syncWithLocation: false,
        queryOptions: { enabled: false },
    });

    const [selectedImage, setSelectedImage] = useState<File | null>(null);
    const [selectedBox, setSelectedBox] = useState<FaceBox | null>(null);
    const [showDetails, setShowDetails] = useState<FaceSimilarItemResponse | null>(null)

    const modal = useModal();

    useEffect(() => {
        if (showDetails && !modal.modalProps.open) {
            setShowDetails(null)
        }
    }, [modal, showDetails])

    const [similarList, setSimilarList] = useState<FaceSimilarItemResponse[]>([])
    const mutation = useCustomMutation<FaceSimilarItemResponse[]>();

    useEffect(() => {
        const call = async () => {
            if (selectedBox && selectedImage) {
                const m = await mutation.mutateAsync({
                    url: "/api/similar-to-image",
                    method: "post",
                    config: {
                        headers: { "Content-Type": "multipart/form-data" }
                    },
                    values: {
                        x: selectedBox?.x,
                        y: selectedBox?.y,
                        w: selectedBox?.w,
                        h: selectedBox?.h,
                        image: selectedImage
                    }
                });
                setSimilarList(m.data)
            }
        }
        call()
    }, [selectedBox, selectedImage])

    return <>
        <Modal
            {...modal.modalProps}
            width={800}
            title={
                showDetails
                    ? "Full size: " + showDetails.w + "×" + showDetails.h + "px"
                    : ""
            }
        >
            {showDetails && (
                <>
                    <FacePicker
                        faceBoxList={[{
                            x: showDetails.x,
                            y: showDetails.y,
                            w: showDetails.w,
                            h: showDetails.h,
                        }]}
                        imageUrl={showDetails.source_url}
                    />
                </>
            )}
        </Modal >
        <FaceSearchPanel
            onSelectedImage={(x) => {
                setSelectedBox(null)
                setSimilarList([])
                setSelectedImage(x.selectedImage)
            }}
            onSelectedFaceBox={(x) => {
                setSelectedBox(x)
            }}
        />
        <List title={<>Similar faces</>}>
            <Table
                {...tableProps}
                dataSource={similarList}
                rowKey="id"
                loading={mutation.mutation.isPending}
            >
                <Table.Column dataIndex="fn" title={"Filename"} />
                <Table.Column
                    dataIndex="distance"
                    title={"Distance"}
                    render={(value) => {
                        return <Tooltip title={value}>{Math.round(Number(value) * 1000) / 1000}</Tooltip>
                    }}
                />
                <Table.Column
                    dataIndex="confidence"
                    title={"Is a face"}
                    render={(value) => {
                        return value + "%"
                    }}
                />
                <Table.Column
                    dataIndex={"model"}
                    title={"Model"}
                    render={(value) => {
                        return value
                    }
                    }
                />
                <Table.Column
                    dataIndex={"preview_url"}
                    title={"Preview"}
                    render={(value, row: FaceSimilarItemResponse) => {
                        return <img
                            src={value}
                            style={{ maxHeight: '100px', maxWidth: '100px' }}
                            onClick={() => {
                                modal.show()
                                setShowDetails(row)
                            }}
                        />
                    }
                    }
                />
            </Table>
        </List>
    </>
};
