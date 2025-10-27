import { useCustomMutation } from "@refinedev/core";
import { Upload, Form, Button, Card, Spin } from "antd";
import { FaceBox, FacePicker } from "./FacePicker";
import { useForm } from "@refinedev/react-hook-form";
import { useState } from "react";
import { UploadOutlined } from "@ant-design/icons";
import { Controller, SubmitHandler, UseFormReturn } from "react-hook-form";
import { getAnalyzeImageApiAnalyzePostUrl, UploadImageResponse } from "../api/generated";
import { UploadFile } from "antd/lib";

interface ImageUploadProps {
    onSelectedImage: (o: { selectedImage: File }) => void
    onSelectedFaceBox: (box: FaceBox) => void
}

interface TForm {
    file: UploadFile[]
}

export const FaceSearchPanel = ({ onSelectedImage: onDone, onSelectedFaceBox: onSelectedFace }: ImageUploadProps) => {
    const form = useForm<TForm>({
        mode: "onChange",
        defaultValues: {
            file: [],
        },
    }) as unknown as UseFormReturn<TForm>;
    const [selectedImageStr, setSelectedImageStr] = useState<string>('');
    const [boxes, setBoxes] = useState<{
        x: number
        y: number
        w: number
        h: number
        color: string
        tooltip: string
        is_strong: boolean
    }[]>([])

    const analyzeImgMut = useCustomMutation<UploadImageResponse>()

    const [selectedBox, setSelectedBox] = useState<{
        x: number
        y: number
        w: number
        h: number
    } | null>(null)

    const onSubmit: SubmitHandler<TForm> = async (data) => {
        const file = data.file[0].originFileObj
        if (!file) {
            return
        }
        onDone({
            selectedImage: file
        })
        setSelectedImageStr(URL.createObjectURL(file))
        setSelectedBox(null)
        setBoxes([])
        const foundBoxes = await analyzeImgMut.mutateAsync({
            method: 'post',
            url: getAnalyzeImageApiAnalyzePostUrl(),
            config: {
                headers: { "Content-Type": "multipart/form-data" }
            },
            values: {
                'file': file
            }
        })
        setBoxes(foundBoxes.data.boxes.map((item) => ({
            x: item.x,
            y: item.y,
            h: item.h,
            w: item.w,
            color: item.similar_faces > 0 ? 'lightgreen' : 'red',
            tooltip: "Found similarities: " + item.similar_faces,
            is_strong: !!selectedBox
                && item.x === selectedBox?.x
                && item.y === selectedBox?.y
                && item.w === selectedBox?.w
                && item.h === selectedBox?.h
        })))
    }

    return (
        <Card title="Search a face" variant="outlined">
            <div>
                <form onSubmit={form.handleSubmit(onSubmit)}>
                    <Form.Item>
                        <Controller
                            name="file"
                            control={form.control}
                            render={({ field }) => {
                                return (
                                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                        <Upload
                                            accept="image/*"
                                            multiple={false}
                                            maxCount={1}
                                            beforeUpload={() => false}
                                            onRemove={() => field.onChange([])}
                                            fileList={field.value}
                                            showUploadList={false}
                                            onChange={({ fileList }) => {
                                                field.onChange(fileList)
                                                form.handleSubmit(onSubmit)();
                                            }}
                                        >
                                            <Button icon={<UploadOutlined />}>Select an image..</Button>
                                        </Upload>
                                    </div>
                                )
                            }}
                        />
                    </Form.Item>
                </form>
                <div>
                    <Spin spinning={analyzeImgMut.mutation.isPending} tip="Analyzing..">
                        <FacePicker
                            imageUrl={selectedImageStr}
                            faceBoxList={boxes}
                            onClickFace={x => {
                                setSelectedBox(x)
                                onSelectedFace(x)
                            }}
                        />
                    </Spin>
                </div>
            </div>
        </Card>
    );
}
