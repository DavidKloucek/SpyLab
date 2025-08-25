import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Router, RouterModule } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatGridListModule } from '@angular/material/grid-list';
import { lastValueFrom } from 'rxjs';
import { MatTableModule } from '@angular/material/table';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import {
    injectMutation,
    injectQuery
} from '@tanstack/angular-query-experimental'
import { AnalyzeResponse, DataService, SimilarFace } from './services/data.service';
import { DetailModalImageComponent, FaceBox } from "./detail-modal-image";
import { ColumnDef } from '@tanstack/angular-table';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { DetailModalComponent, DetailModalData } from './detail-modal.component';
import { MatTabsModule } from '@angular/material/tabs';

@Component({
    selector: 'face-list-component',
    standalone: true,
    imports: [CommonModule, HttpClientModule, RouterModule, MatCardModule, MatButtonModule, MatGridListModule, FormsModule, MatIconModule, DetailModalImageComponent, MatChipsModule, MatTableModule, MatTabsModule, MatProgressSpinnerModule],
    templateUrl: './finder.component.html',
})
export class FinderComponent {
    router = inject(Router);
    api = inject(DataService)
    dialog = inject(MatDialog);
    columns: ColumnDef<any>[] = [
        { id: 'id', header: 'ID' },
        { id: 'fn', header: 'Source' },
        { id: 'preview_url', header: 'Preview' },
        { id: 'is_same', header: 'Matches' },
        { id: 'distance', header: 'Distance' },
    ];
    tableCols = this.columns.map((col) => col.id) as string[];
    selectedBox = signal<FaceBox | null>(null)
    analyzedImage = signal<AnalyzeResponse | null>(null)
    selectedImageStr = signal<string>("")
    selectedImage = signal<File | null>(null)

    tableData = computed<SimilarFace[]>(() => {
        return this.findByImageQry.data() ?? []
    })

    analyzedBoxes = computed(() => {
        return this.analyzedImage()?.boxes.map<FaceBox>(item => ({
            x: item.x,
            y: item.y,
            h: item.h,
            w: item.w,
            color: item.similar_faces > 0 ? 'red' : 'lightgreen',
            tooltip: "Found similarities: " + item.similar_faces,
            is_strong: !!this.selectedBox()
                && item.x === this.selectedBox()?.x
                && item.y === this.selectedBox()?.y
                && item.w === this.selectedBox()?.w
                && item.h === this.selectedBox()?.h
        })) ?? []
    })

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        if (input.files && input.files.length > 0) {
            this.selectedImage.set(input.files[0])
        }
    }

    onDrop(event: DragEvent): void {
        event.preventDefault();
        if (event.dataTransfer?.files && event.dataTransfer.files.length > 0) {
            this.selectedImage.set(event.dataTransfer.files[0]);
        }
    }

    findByImageQry = injectQuery(() => ({
        queryKey: ['find-by-image', this.selectedBox()],
        enabled: this.selectedBox() !== null && this.selectedImage() !== null,
        queryFn: ({ signal }) => {
            return lastValueFrom(this.api.findSimilarToImage(this.selectedImage()!, this.selectedBox()!.x, this.selectedBox()!.y, this.selectedBox()!.w, this.selectedBox()!.h))
        }
    }))

    analyzeImgMut = injectMutation(() => ({
        mutationFn: (file: File) => {
            return lastValueFrom(this.api.analyzeImage(file))
        },
        onSuccess: (data) => {
            this.analyzedImage.set(data)
            this.selectedImageStr.set(URL.createObjectURL(this.selectedImage()!))
        },
        onError: (error) => {
            console.error(error);
        },
    }))

    onSubmit(): void {
        if (this.selectedImage()) {
            this.analyzeImgMut.mutate(this.selectedImage()!);
        }
    }

    onDragOver(event: DragEvent): void {
        event.preventDefault();
    }

    openDialog(data: SimilarFace) {
        this.dialog.open<DetailModalComponent, DetailModalData>(DetailModalComponent, {
            data: {
                source_url: data.source_url,
                faces: [data]
            },
        });
    }

    clickFace(face: FaceBox) {
        this.selectedBox.set(face)
    }
}
