import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoCopyPasteDirective } from './no-copy-paste.directive';

@Component({
  standalone: true,
  imports: [NoCopyPasteDirective],
  template: `<div appNoCopyPaste>contenido</div>`,
})
class HostComponent {}

describe('NoCopyPasteDirective', () => {
  let fixture: ComponentFixture<HostComponent>;
  let el: HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostComponent] });
    fixture = TestBed.createComponent(HostComponent);
    fixture.detectChanges();
    el = fixture.nativeElement.querySelector('div');
  });

  it.each(['copy', 'cut', 'paste', 'dragstart', 'contextmenu'])(
    'cancela el evento %s',
    (type) => {
      const event = new Event(type, { cancelable: true });
      el.dispatchEvent(event);
      expect(event.defaultPrevented).toBe(true);
    },
  );
});
