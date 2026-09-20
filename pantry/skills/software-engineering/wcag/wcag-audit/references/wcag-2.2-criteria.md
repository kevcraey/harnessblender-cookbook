# WCAG 2.2 Level A & AA Success Criteria

This reference list contains all Level A and AA criteria from WCAG 2.2, optimized for AI checking.

## 1. Perceivable

### 1.1 Text Alternatives

- **1.1.1 Non-text Content (A)**: All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.

### 1.2 Time-based Media

- **1.2.1 Audio-only and Video-only (Prerecorded) (A)**
- **1.2.2 Captions (Prerecorded) (A)**
- **1.2.3 Audio Description or Media Alternative (Prerecorded) (A)**
- **1.2.4 Captions (Live) (AA)**
- **1.2.5 Audio Description (Prerecorded) (AA)**

### 1.3 Adaptable

- **1.3.1 Info and Relationships (A)**: Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text.
- **1.3.2 Meaningful Sequence (A)**: When the sequence in which content is presented affects its meaning, a correct reading sequence can be programmatically determined.
- **1.3.3 Sensory Characteristics (A)**: Instructions provided for understanding and operating content do not rely solely on sensory characteristics of components such as shape, color, size, visual location, orientation, or sound.
- **1.3.4 Orientation (AA)**: Content does not restrict its view and operation to a single display orientation, such as portrait or landscape, unless a specific display orientation is essential.
- **1.3.5 Identify Input Purpose (AA)**: The purpose of each input field collecting information about the user can be programmatically determined when the field serves a purpose identified in the Input Purposes for User Interface Components section.

### 1.4 Distinguishable

- **1.4.1 Use of Color (A)**: Color is not used as the only visual means of conveying information, indicating an action, prompting a response, or distinguishing a visual element.
- **1.4.2 Audio Control (A)**: If any audio on a Web page plays automatically for more than 3 seconds, either a mechanism is available to pause or stop the audio, or a mechanism is available to control audio volume independently from the overall system volume level.
- **1.4.3 Contrast (Minimum) (AA)**: The visual presentation of text and images of text has a contrast ratio of at least 4.5:1 (large text 3:1).
- **1.4.4 Resize text (AA)**: Except for captions and images of text, text can be resized without assistive technology up to 200 percent without loss of content or functionality.
- **1.4.5 Images of Text (AA)**: If the technologies being used can achieve the visual presentation, text is used to convey information rather than images of text.
- **1.4.10 Reflow (AA)**: Content can be presented without loss of information or functionality, and without requiring scrolling in two dimensions for various screen widths (down to 320 CSS pixels).
- **1.4.11 Non-text Contrast (AA)**: The visual presentation of user interface components and graphical objects has a contrast ratio of at least 3:1 against adjacent color(s).
- **1.4.12 Text Spacing (AA)**: No loss of content or functionality occurs by setting line height, spacing following paragraphs, letter spacing, and word spacing to specific values.
- **1.4.13 Content on Hover or Focus (AA)**: Where receiving and then removing pointer hover or keyboard focus triggers additional content to become visible and then hidden, mechanisms for dismissal, hoverability, and persistence exist.

## 2. Operable

### 2.1 Keyboard Accessible

- **2.1.1 Keyboard (A)**: All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes.
- **2.1.2 No Keyboard Trap (A)**: If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface.
- **2.1.4 Character Key Shortcuts (A)**: If a keyboard shortcut is implemented in content using only letter (including upper- and lower-case letters), punctuation, numbers, or symbol characters, then the user can turn it off, remap it, or activate it only on focus.

### 2.2 Enough Time

- **2.2.1 Timing Adjustable (A)**: For each time limit that is set by the content, the user is allowed to turn off, adjust, or extend the limit.
- **2.2.2 Pause, Stop, Hide (A)**: For moving, blinking, scrolling, or auto-updating information, there is a mechanism for the user to pause, stop, or hide it.

### 2.3 Seizures and Physical Reactions

- **2.3.1 Three Flashes or Below Threshold (A)**: Web pages do not contain anything that flashes more than three times in any one second period, or the flash is below the general flash and red flash thresholds.

### 2.4 Navigable

- **2.4.1 Bypass Blocks (A)**: A mechanism is available to bypass blocks of content that are repeated on multiple Web pages.
- **2.4.2 Page Titled (A)**: Web pages have titles that describe topic or purpose.
- **2.4.3 Focus Order (A)**: If a Web page can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.
- **2.4.4 Link Purpose (In Context) (A)**: The purpose of each link can be determined from the link text alone or from the link text together with its programmatically determined link context.
- **2.4.5 Multiple Ways (AA)**: More than one way is available to locate a Web page within a set of Web pages.
- **2.4.6 Headings and Labels (AA)**: Headings and labels describe topic or purpose.
- **2.4.7 Focus Visible (AA)**: Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.
- **2.4.11 Focus Not Obscured (Minimum) (AA)**: (WCAG 2.2) When a user interface component receives keyboard focus, the component is not entirely hidden due to author-created content.
- **2.4.13 Focus Appearance (AA)**: (WCAG 2.2) Focus indicators have sufficient size and contrast.

### 2.5 Input Modalities

- **2.5.1 Pointer Gestures (A)**: All functionality that uses multipoint or path-based gestures for operation can be operated with a single pointer without a path-based gesture.
- **2.5.2 Pointer Cancellation (A)**: For functionality that can be operated using a single pointer, completion of the function is on the up-event.
- **2.5.3 Label in Name (A)**: For user interface components with labels that include text or images of text, the name contains the text that is presented visually.
- **2.5.4 Motion Actuation (A)**: Functionality that can be operated by device motion or user motion can also be operated by user interface components and responding to the motion can be disabled.
- **2.5.7 Dragging Movements (AA)**: (WCAG 2.2) All functionality that uses a dragging movement for operation can be achieved by a single pointer without dragging.
- **2.5.8 Target Size (Minimum) (AA)**: (WCAG 2.2) The size of the target for pointer inputs is at least 24 by 24 CSS pixels.

## 3. Understandable

### 3.1 Readable

- **3.1.1 Language of Page (A)**: The default human language of each Web page can be programmatically determined.
- **3.1.2 Language of Parts (AA)**: The human language of each passage or phrase in the content can be programmatically determined.

### 3.2 Predictable

- **3.2.1 On Focus (A)**: When any user interface component receives focus, it does not initiate a change of context.
- **3.2.2 On Input (A)**: Changing the setting of any user interface component does not automatically cause a change of context unless the user has been advised of the behavior before using the component.
- **3.2.3 Consistent Navigation (AA)**: Navigational mechanisms that are repeated on multiple Web pages within a set of Web pages occur in the same relative order each time they are repeated.
- **3.2.4 Consistent Identification (AA)**: Components that have the same functionality within a set of Web pages are identified consistently.

### 3.3 Input Assistance

- **3.3.1 Error Identification (A)**: If an input error is automatically detected, the item that is in error is identified and the error is described to the user in text.
- **3.3.2 Labels or Instructions (A)**: Labels or instructions are provided when content requires user input.
- **3.3.3 Error Suggestion (AA)**: If an input error is automatically detected and suggestions for correction are known, then the suggestions are provided to the user, unless it would jeopardize the security or purpose of the content.
- **3.3.4 Error Prevention (Legal, Financial, Data) (AA)**: For Web pages that cause legal commitments or financial transactions for the user to occur, that modify or delete user-controllable data in data storage systems, or that submit user test responses, checks are available.
- **3.3.7 Redundant Entry (A)**: (WCAG 2.2) Information previously entered by or provided to the user that is required to be entered again in the same process is either auto-populated or available for the user to select.

## 4. Robust

### 4.1 Compatible

- **4.1.1 Parsing (A)**: (Note: This criterion was deprecated in WCAG 2.2, but ensuring valid markup is still best practice for 4.1.2).
- **4.1.2 Name, Role, Value (A)**: For all user interface components (including but not limited to: form elements, links and components generated by scripts), the name and role can be programmatically determined; states, properties, and values that can be set by the user can be programmatically set; and notification of changes to these items is available to user agents, including assistive technologies.
- **4.1.3 Status Messages (AA)**: In content implemented using markup languages, status messages can be programmatically determined through role or properties such that they can be presented to the user by assistive technologies without receiving focus.
