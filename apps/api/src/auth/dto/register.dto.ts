import {
  IsEmail,
  IsNotEmpty,
  IsString,
  IsStrongPassword,
  MaxLength,
  MinLength,
} from 'class-validator';

export class RegisterDto {
  @IsString()
  @IsNotEmpty()
  @IsEmail()
  email: string;

  @IsString()
  @IsStrongPassword({
    minLength: 10,
    minNumbers: 1,
    minLowercase: 1,
    minUppercase: 1,
    minSymbols: 1,
  })
  password: string;

  @IsString()
  @IsNotEmpty()
  @MinLength(3)
  @MaxLength(20)
  name: string;
}
