import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatDialogActions, MatDialogClose, MatDialogContent, MatDialogTitle, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DetailModalImageComponent, FaceBox } from "./detail-modal-image";

export interface DetailModalData {
    source_url: string
    faces: FaceBox[]
}

@Component({
    selector: 'detail-modal',
    standalone: true,
    imports: [
        CommonModule,
        MatButtonModule,
        MatDialogActions,
        MatDialogClose,
        MatDialogContent,
        MatDialogTitle,
        DetailModalImageComponent
    ],
    template: `
    <h2 mat-dialog-title>Detail</h2>
    <mat-dialog-content class="dialog-content">
        <detail-modal-image
            [sourceUrl]="data.source_url"
            [itemData]="data.faces"
        />
    </mat-dialog-content>
    <mat-dialog-actions>
        <button mat-button [mat-dialog-close]="close()" cdkFocusInitial>Ok</button>
    </mat-dialog-actions>
    `,
    styles: [`
        .dialog-content {
            display: flex;
            flex-direction: column;
            align-items: center;
        }
    `],
})
export class DetailModalComponent {

    data = inject<DetailModalData>(MAT_DIALOG_DATA);

    close() {
    }
}
