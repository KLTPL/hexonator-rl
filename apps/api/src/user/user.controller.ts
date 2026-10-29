import { Controller, Patch, Req, Body } from '@nestjs/common';
import { UpdateUserDto } from './dto/update-user.dto';
import { UserService } from './user.service';

@Controller('user')
export class UserController {
  constructor(private readonly userService: UserService) {}
  @Patch()
  updateProfile(
    @Req() req: { user: { id: string } },
    @Body() dto: UpdateUserDto,
  ) {
    return this.userService.update(req.user.id, dto);
  }
}
