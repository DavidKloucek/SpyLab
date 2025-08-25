import { AfterViewInit, Component, effect, signal } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { MatToolbar } from '@angular/material/toolbar';
import { MatButton } from '@angular/material/button';

@Component({
    selector: 'app-root',
    imports: [RouterOutlet, MatToolbar, MatButton, RouterLink],
    providers: [],
    templateUrl: './app.component.html',
    standalone: true,
    styleUrl: './app.component.css'
})
export class AppComponent {
    title = 'SpyLab';
}
